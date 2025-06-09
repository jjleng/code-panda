import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { neighborhoods } from '@/data/neighborhoods';

const NeighborhoodsSection = () => {
  return (
    <section className="section-padding bg-accent/30">
      <div className="container-max">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 text-primary">Austin Neighborhoods</h2>
          <p className="text-xl text-muted-foreground">
            Explore the diverse communities that make Austin unique
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {neighborhoods.map((neighborhood, index) => (
            <Card key={index} className="text-center hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                  <neighborhood.icon className="h-6 w-6" />
                </div>
                <CardTitle className="text-xl">{neighborhood.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base mb-4">
                  {neighborhood.description}
                </CardDescription>
                <div className="flex flex-wrap gap-2 justify-center">
                  {neighborhood.highlights.map((highlight, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      {highlight}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default NeighborhoodsSection;
