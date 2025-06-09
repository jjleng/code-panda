import HeroSection from '@/components/HeroSection';
import AboutSection from '@/components/AboutSection';
import ServicesSection from '@/components/ServicesSection';
import FeaturedListingsSection from '@/components/FeaturedListingsSection';
import TestimonialsSection from '@/components/TestimonialsSection';
import NeighborhoodsSection from '@/components/NeighborhoodsSection';
import ContactSection from '@/components/ContactSection';
import Footer from '@/components/Footer';

const Index = () => {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <AboutSection />
      <ServicesSection />
      <FeaturedListingsSection />
      <TestimonialsSection />
      <NeighborhoodsSection />
      <ContactSection />
      <Footer />
    </div>
  );
};

export default Index;
