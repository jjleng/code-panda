import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowRight } from 'lucide-react';
import { featuredListings } from '@/data/listings';

const FeaturedListingsSection = () => {
  return (
    <section className="section-padding bg-muted/30">
      <div className="container-max">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 text-primary">Featured Listings</h2>
          <p className="text-xl text-muted-foreground">
            Discover some of Austin's finest available properties
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredListings.map((listing) => (
            <Card key={listing.id} className="overflow-hidden hover:shadow-lg transition-shadow">
              <div className="relative">
                <img 
                  src={listing.image} 
                  alt={listing.address}
                  className="w-full h-48 object-cover"
                />
                <Badge className="absolute top-3 left-3 bg-secondary text-secondary-foreground">
                  {listing.neighborhood}
                </Badge>
              </div>
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-primary mb-2">{listing.price}</div>
                <div className="text-sm text-muted-foreground mb-3">{listing.address}</div>
                <div className="flex justify-between text-sm">
                  <span>{listing.beds} beds</span>
                  <span>{listing.baths} baths</span>
                  <span>{listing.sqft} sqft</span>
                </div>
                <Button className="w-full mt-4" variant="outline">
                  View Details
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
        
        <div className="text-center mt-8">
          <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90">
            View All Listings
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
    </section>
  );
};

export default FeaturedListingsSection;
