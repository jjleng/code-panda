import { Card, CardContent } from '@/components/ui/card';
import { Star } from 'lucide-react';
import { testimonials } from '@/data/testimonials';

const TestimonialsSection = () => {
  return (
    <section className="section-padding">
      <div className="container-max">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 text-primary">What Our Clients Say</h2>
          <p className="text-xl text-muted-foreground">
            Real experiences from satisfied Austin homeowners
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <Card key={index} className="text-center hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-center mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="h-5 w-5 fill-secondary text-secondary" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-4 italic">"{testimonial.text}"</p>
                <div className="font-semibold">{testimonial.name}</div>
                <div className="text-sm text-muted-foreground">{testimonial.location}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TestimonialsSection;
