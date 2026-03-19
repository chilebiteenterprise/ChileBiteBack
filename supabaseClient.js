// CLIENTE DE SUPABASE (Frontend - React/Astro)
// Instala la dependencia antes: npm install @supabase/supabase-js

import { createClient } from '@supabase/supabase-js'

// Estas variables deben estar en tu archivo .env del frontend
const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL
const supabaseAnonKey = import.meta.env.PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  console.error("Faltan las variables de entorno de Supabase")
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

/**
 * Ejemplo de uso para Login con Google:
 * 
 * const signInWithGoogle = async () => {
 *   const { error } = await supabase.auth.signInWithOAuth({
 *     provider: 'google',
 *   })
 *   if (error) console.error('Error:', error.message)
 * }
 */
