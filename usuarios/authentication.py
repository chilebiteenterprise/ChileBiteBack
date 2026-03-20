
import jwt
from jwt import PyJWKClient
import base64
from django.conf import settings
from rest_framework import authentication, exceptions

class AuthUser:
    """
    Clase simple para simular un modelo de usuario de Django.
    Almacena los datos extraídos directamente del JWT de Supabase.
    """
    def __init__(self, token_payload):
        self.id = token_payload.get('sub')
        self.email = token_payload.get('email')
        
        # Extraer metadatos
        self.user_metadata = token_payload.get('user_metadata', {})
        self.app_metadata = token_payload.get('app_metadata', {})
        
        # El rol puede venir en app_metadata o user_metadata dependiendo de la configuración
        # Buscar tanto 'role' como 'rol' por inconsistencias de idioma
        self.role = (
            self.user_metadata.get('role') or 
            self.user_metadata.get('rol') or 
            self.app_metadata.get('role') or 
            'user'
        )
        if str(self.role).lower() == 'admin':
            self.role = 'admin'
            
        # 🚨 PARCHE: Si el JWT no contiene el rol 'admin', buscarlo directamente en la BD
        if self.role != 'admin':
            # We will fetch this in the authenticate() method below
            self._needs_role_check = True

        self.username = self.user_metadata.get('user_name', self.email.split('@')[0] if self.email else 'user')
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def __str__(self):
        return f"{self.email} ({self.id})"

class SupabaseAuthentication(authentication.BaseAuthentication):
    """
    Autenticación sin estado (Stateless). 
    Valida criptográficamente el JWT contra el JWKS de Supabase.
    """
    
    def authenticate_header(self, request):
        return 'Bearer'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        parts = auth_header.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed("Encabezado Authorization inválido. Debe ser 'Bearer <token>'")

        token = parts[1]

        try:
            supabase_url = getattr(settings, 'SUPABASE_URL', None)
            if not supabase_url:
                raise exceptions.AuthenticationFailed("SUPABASE_URL no está configurado en el servidor")

            # Obtener y cachear las claves públicas (JWKS) desde Supabase
            jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Validar robustamente la firma de JWT
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["HS256", "RS256", "ES256"],
                audience="authenticated", 
                options={"verify_signature": True},
                leeway=60
            )

        except jwt.ExpiredSignatureError:
            print("JWT Error: El token ha expirado")
            raise exceptions.AuthenticationFailed("El token ha expirado")
        except jwt.InvalidSignatureError:
            print("JWT Error: La firma del token es inválida")
            raise exceptions.AuthenticationFailed("La firma del token es inválida")
        except jwt.InvalidAudienceError:
            # En caso de que el token no tenga 'authenticated' audience
            try:
                payload = jwt.decode(token, signing_key.key, algorithms=["HS256", "RS256", "ES256"], options={"verify_signature": True, "verify_aud": False}, leeway=60)
            except Exception as e:
                print(f"JWT Error en fallback de Audience: {str(e)}")
                raise exceptions.AuthenticationFailed(f"Error de JWT: {str(e)}")
        except jwt.InvalidTokenError as e:
            print(f"JWT Error Token Inválido: {str(e)}")
            raise exceptions.AuthenticationFailed(f"Token inválido: {str(e)}")
        except Exception as e:
            print(f"JWT Error general: {str(e)}")
            import traceback
            traceback.print_exc()
            raise exceptions.AuthenticationFailed(f"Fallo en la decodificación del Token: {str(e)}")

        supabase_user_id = payload.get('sub')
        if not supabase_user_id:
            raise exceptions.AuthenticationFailed("El token no contiene un 'sub' válido")

        # Construir y retornar el usuario en memoria
        user = AuthUser(payload)
        
        if getattr(user, '_needs_role_check', False):
            try:
                import requests
                url = getattr(settings, 'SUPABASE_URL', None)
                key = getattr(settings, 'SUPABASE_ANON_KEY', None)
                if not url or not key:
                    raise exceptions.AuthenticationFailed("Falta URL o Key de Supabase en settings.")
                    
                if url and key and user.id:
                    res = requests.get(
                        f"{url.rstrip('/')}/rest/v1/profiles?id=eq.{user.id}&select=role",
                        headers={
                            "apikey": key,
                            "Authorization": f"Bearer {token}"
                        },
                        timeout=3
                    )
                    if res.status_code == 200:
                        data = res.json()
                        if not data:
                            raise exceptions.AuthenticationFailed(f"No se encontró perfil para id {user.id}")
                        r = data[0].get('role')
                        if r and str(r).lower() == 'admin':
                            user.role = 'admin'
                        else:
                            raise exceptions.AuthenticationFailed(f"El perfil existe, pero el rol es '{r}', no admin. Data: {data}")
                    else:
                        raise exceptions.AuthenticationFailed(f"Error de Supabase REST ({res.status_code}): {res.text}")
            except Exception as e:
                # Si fallamos levantando AuthenticationFailed, dejar que pase para mostrarlo
                if isinstance(e, exceptions.AuthenticationFailed):
                    raise e
                raise exceptions.AuthenticationFailed(f"Error crítico conectando a Supabase DB: {str(e)}")
        
        return (user, token)