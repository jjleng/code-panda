import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Home, Search, Users } from 'lucide-react';

const ServicesSection = () => {
  const services = [
    {
      icon: <Home className="h-8 w-8 text-primary" />,
      title: "Home Buying Assistance",
      description: "From pre-approval to closing, we guide you through every step of the home buying process."
    },
    {
      icon: <Search className="h-8 w-8 text-primary" />,
      title: "Property Search",
      description: "Access to exclusive listings and off-market properties that match your specific criteria."
    },
    {
      icon: <Users className="h-8 w-8 text-primary" />,
      title: "Neighborhood Guidance",
      description: "Expert insights into Austin neighborhoods, schools, amenities, and future development plans."
    }
  ];

  return (
    <section className="section-padding">
      <div className="container-max">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 text-primary">Our Services</h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Comprehensive real estate services tailored to Austin home buyers
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {services.map((service, index) => (
            <Card key={index} className="text-center hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                  {service.icon}
                </div>
                <CardTitle className="text-xl">{service.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  {service.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ServicesSection;
