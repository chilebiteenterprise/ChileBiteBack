# Supabase Auth Integration Guide

This guide explains how to connect your ChileBite Frontend (Astro/React) with the Django Backend using Supabase as the source of truth for identity.

## 1. Backend Configuration

### Secret JWT
Para que el backend pueda validar los tokens de Supabase, necesitas configurar el `SUPABASE_JWT_SECRET` en tu archivo `.env` o en `settings.py`.

**¿Dónde encontrarlo?**
1. Ve a tu [Supabase Dashboard](https://supabase.com/dashboard).
2. Selecciona tu proyecto.
3. Ve a **Settings > API**.
4. Busca la sección **JWT Settings** y copia el **JWT Secret**.

---

## 2. Frontend Snippets (React)

### Login con Google
```javascript
import { supabase } from './supabaseClient'

async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: 'http://localhost:3000/auth/callback'
    }
  })
}
```

### Registro con Email/Password
```javascript
async function signUp(email, password) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })
}
```

### Llamada a la API de Django (Autenticada)
Una vez logueado en Supabase, obtienes la sesión y envías el token a Django:

```javascript
const { data: { session } } = await supabase.auth.getSession()

if (session) {
  const response = await fetch('http://localhost:8000/usuarios/perfil/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  })
  const profile = await response.json()
  console.log('Perfil de ChileBite:', profile)
}
```

---

## 3. Flujo de Trabajo
1. **Frontend** autentica con Supabase.
2. **Frontend** guarda el `access_token`.
3. **Frontend** envía el `access_token` a cualquier endpoint de Django.
4. **Django** valida el token, crea el usuario localmente si no existe (**JIT Provisioning**) y procesa la petición.
