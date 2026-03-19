-- ======================================================
-- MIGRACIÓN: Añadir campos faltantes a profiles
-- Ejecutar en: Supabase Dashboard > SQL Editor
-- ======================================================

-- 1. Añadir columnas que faltaban
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS nombres text,
  ADD COLUMN IF NOT EXISTS apellido_paterno text,
  ADD COLUMN IF NOT EXISTS apellido_materno text,
  ADD COLUMN IF NOT EXISTS bio text,
  ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone default now();

-- 2. Política RLS para que el trigger pueda INSERT (si aún no existe)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'profiles' AND policyname = 'Service can insert profiles'
  ) THEN
    CREATE POLICY "Service can insert profiles"
      ON public.profiles
      FOR INSERT
      WITH CHECK (true);
  END IF;
END
$$;

-- 3. Trigger: sync user_metadata → profiles en cada UPDATE de auth.users
--    Se dispara cuando el usuario llama supabase.auth.updateUser({data: {...}})
CREATE OR REPLACE FUNCTION public.handle_user_update()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE public.profiles
  SET
    username         = COALESCE(NEW.raw_user_meta_data->>'user_name', profiles.username),
    nombres          = COALESCE(NEW.raw_user_meta_data->>'nombres', profiles.nombres),
    apellido_paterno = COALESCE(NEW.raw_user_meta_data->>'apellido_paterno', profiles.apellido_paterno),
    apellido_materno = COALESCE(NEW.raw_user_meta_data->>'apellido_materno', profiles.apellido_materno),
    bio              = COALESCE(NEW.raw_user_meta_data->>'bio', profiles.bio),
    avatar_url       = COALESCE(NEW.raw_user_meta_data->>'avatar_url', profiles.avatar_url),
    updated_at       = now()
  WHERE id = NEW.id;

  RETURN NEW;
END;
$$;

-- Eliminar trigger previo si existe para evitar duplicados
DROP TRIGGER IF EXISTS on_auth_user_updated ON auth.users;

CREATE TRIGGER on_auth_user_updated
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  EXECUTE PROCEDURE public.handle_user_update();

-- 4. Trigger mejorado para nuevo usuario (incluye username desde metadata)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, username, avatar_url)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(
      NEW.raw_user_meta_data->>'user_name',
      NEW.raw_user_meta_data->>'name',
      split_part(NEW.email, '@', 1)
    ),
    NEW.raw_user_meta_data->>'avatar_url'
  )
  ON CONFLICT (id) DO NOTHING;

  RETURN NEW;
END;
$$;

-- 5. Solucionar error de "Infinite Recursion"
--    El usuario tenía una política antigua llamada "Admins can view all profiles"
--    que hacía un SELECT a la misma tabla profiles, causando un bucle infinito.
--    La eliminamos preventivamente.
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;

-- 6. Política para que usuarios autenticados puedan ver TODOS los perfiles
--    (necesario si hay features sociales; ajustar según necesidad)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'profiles' AND policyname = 'Authenticated users can read all profiles'
  ) THEN
    CREATE POLICY "Authenticated users can read all profiles"
      ON public.profiles
      FOR SELECT
      TO authenticated
      USING (true);
  END IF;
END
$$;


-- ======================================================
-- STORAGE: Políticas para bucket 'avatars'
-- ======================================================
-- IMPORTANTE: Ejecutar DESPUÉS de crear el bucket 'avatars' en Supabase Dashboard.
-- Dashboard → Storage → avatars → Policies → Add policy (o ejecutar este SQL).
-- ======================================================

-- ① Acceso público anónimo a imágenes JPG/PNG en la carpeta 'public/'
--    Patrón: avatars/public/*.jpg  |  Quién: anon (sin login)
--    Caso de uso: imágenes de portada, logos, assets públicos del sitio
CREATE POLICY "Public read of images in public folder"
  ON storage.objects
  FOR SELECT
  TO anon
  USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = 'public'
    AND (name LIKE '%.jpg' OR name LIKE '%.jpeg' OR name LIKE '%.png' OR name LIKE '%.webp')
  );

-- ② Usuario solo accede a su propia carpeta raíz (nombrada como su UID)
--    Patrón: avatars/{uid}/*
--    Quién: el propio usuario autenticado
--    ✅ Esta es la política activa para avatares de ChileBite
CREATE POLICY "Users manage only their own folder"
  ON storage.objects
  FOR ALL          -- SELECT, INSERT, UPDATE, DELETE
  TO authenticated
  USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::text
  )
  WITH CHECK (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

-- ③ Cualquier usuario autenticado puede leer archivos de cualquier carpeta
--    Patrón: avatars/**
--    Quién: cualquier usuario con sesión iniciada
--    Caso de uso: ver avatares de otros chefs en la galería de recetas
CREATE POLICY "Authenticated users can read all avatars"
  ON storage.objects
  FOR SELECT
  TO authenticated
  USING (bucket_id = 'avatars');

-- ④ Solo un usuario admin específico puede acceder a admin/assets/
--    Patrón: avatars/admin/assets/*
--    Reemplaza 'REEMPLAZAR-CON-UUID-ADMIN' con el UUID real del admin en Supabase Dashboard
--    Dashboard → Authentication → Users → copiar el UUID del usuario admin
CREATE POLICY "Admin user only access to admin/assets folder"
  ON storage.objects
  FOR ALL
  TO authenticated
  USING (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = 'admin'
    AND (storage.foldername(name))[2] = 'assets'
    AND auth.uid() = 'REEMPLAZAR-CON-UUID-ADMIN'::uuid
  )
  WITH CHECK (
    bucket_id = 'avatars'
    AND (storage.foldername(name))[1] = 'admin'
    AND (storage.foldername(name))[2] = 'assets'
    AND auth.uid() = 'REEMPLAZAR-CON-UUID-ADMIN'::uuid
  );

-- ⑤ Acceso a un archivo específico para un usuario específico
--    Patrón: avatars/shared/logo-chilebite.png
--    Quién: un único usuario (por UUID)
--    Caso de uso: documento privado compartido, asset exclusivo
CREATE POLICY "Specific user access to specific file"
  ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'avatars'
    AND name = 'shared/logo-chilebite.png'   -- reemplazar con la ruta real del archivo
    AND auth.uid() = 'REEMPLAZAR-CON-UUID-USUARIO'::uuid
  );
