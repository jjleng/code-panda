import { Button } from '@/components/ui/button';
import { Phone, ArrowRight } from 'lucide-react';

const HeroSection = () => {
  return (
    <section className="relative h-screen flex items-center justify-center text-white">
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1531971589569-0d9370cbe1e5?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80')"
        }}
      />
      <div className="absolute inset-0 hero-gradient" />
      
      <div className="relative z-10 text-center max-w-4xl mx-auto px-4">
        <h1 className="text-5xl md:text-7xl font-bold mb-6">
          Find Your Perfect Home in Austin
        </h1>
        <p className="text-xl md:text-2xl mb-8 text-blue-100">
          YellowFin Real Estate - Your trusted partner in Austin home buying
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" className="bg-secondary text-secondary-foreground hover:bg-secondary/90 text-lg px-8 py-3">
            Start Your Search
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
          <Button size="lg" variant="outline" className="bg-white/10 text-white border-white hover:bg-white hover:text-primary text-lg px-8 py-3">
            <Phone className="mr-2 h-5 w-5" />
            Call (512) 555-0123
          </Button>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
