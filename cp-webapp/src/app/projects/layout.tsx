import { AppSidebar } from '@/components/side-bar/app-sidebar';

export default function ProjectsLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppSidebar />
      {children}
    </>
  );
}
