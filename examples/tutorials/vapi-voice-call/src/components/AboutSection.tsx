import { CheckCircle } from 'lucide-react';

const AboutSection = () => {
  return (
    <section className="section-padding bg-accent/30">
      <div className="container-max">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-4xl font-bold mb-6 text-primary">About YellowFin Real Estate</h2>
            <p className="text-lg mb-6 text-muted-foreground">
              With over 15 years of experience in the Austin real estate market, YellowFin Real Estate 
              specializes in helping buyers navigate the competitive Austin housing market with confidence.
            </p>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-6 w-6 text-secondary" />
                <span className="text-lg">Local Austin market expertise since 2008</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="h-6 w-6 text-secondary" />
                <span className="text-lg">Buyer-focused approach and personalized service</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="h-6 w-6 text-secondary" />
                <span className="text-lg">Comprehensive neighborhood knowledge</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="h-6 w-6 text-secondary" />
                <span className="text-lg">500+ successful home purchases facilitated</span>
              </div>
            </div>
          </div>
          <div>
            <img 
              src="https://images.unsplash.com/photo-1560518883-ce09059eeffa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
              alt="Austin real estate team"
              className="rounded-lg shadow-lg w-full"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
