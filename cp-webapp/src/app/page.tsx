'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.push('/projects/new');
  }, [router]);

  // Return a simple loading state while redirecting
  return <div className="flex min-h-screen items-center justify-center"></div>;
}
