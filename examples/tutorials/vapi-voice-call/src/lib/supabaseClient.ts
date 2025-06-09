import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://xqsalouztsgbzflnmjlf.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhxc2Fsb3V6dHNnYnpmbG5tamxmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxOTIxMzQsImV4cCI6MjA1Nzc2ODEzNH0.LfATVPNWx2wk65RHmLv6TF0AC1-mtJ86EbauV7Q5VTc';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
