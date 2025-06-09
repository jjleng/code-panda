import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Phone, Mail, MapPin, ArrowRight } from 'lucide-react';
import { useContactForm } from '@/hooks/useContactForm';

const ContactSection = () => {
  const { formData, handleInputChange, handleSubmit } = useContactForm();

  return (
    <section className="section-padding bg-primary text-white">
      <div className="container-max">
        <div className="grid lg:grid-cols-2 gap-12">
          {/* Contact Information */}
          <div>
            <h2 className="text-4xl font-bold mb-6">Get Started Today</h2>
            <p className="text-xl mb-8 text-blue-100">
              Ready to find your dream home in Austin? Contact YellowFin Real Estate and let our 
              experienced team guide you through the process.
            </p>
            
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center">
                  <Phone className="h-6 w-6" />
                </div>
                <div>
                  <div className="font-semibold">Phone</div>
                  <div className="text-blue-100">(512) 555-0123</div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center">
                  <Mail className="h-6 w-6" />
                </div>
                <div>
                  <div className="font-semibold">Email</div>
                  <div className="text-blue-100">info@yellowfinrealty.com</div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center">
                  <MapPin className="h-6 w-6" />
                </div>
                <div>
                  <div className="font-semibold">Office</div>
                  <div className="text-blue-100">
                    2901 Capital of Texas Hwy<br />
                    Austin, TX 78746
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Lead Capture Form */}
          <div>
            <Card className="bg-white text-foreground">
              <CardHeader>
                <CardTitle className="text-2xl text-primary">Start Your Home Search</CardTitle>
                <CardDescription>
                  Fill out the form below and we'll contact you within 24 hours to discuss your needs.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">Full Name *</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        placeholder="Your full name"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="phone">Phone Number *</Label>
                      <Input
                        id="phone"
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        placeholder="(512) 555-0123"
                        required
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="email">Email Address *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      placeholder="your.email@example.com"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="interests">What are you looking for?</Label>
                    <Select onValueChange={(value) => handleInputChange('interests', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select your interests" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="first-time-buyer">First-time home buyer</SelectItem>
                        <SelectItem value="upgrading">Upgrading to larger home</SelectItem>
                        <SelectItem value="downsizing">Downsizing</SelectItem>
                        <SelectItem value="investment">Investment property</SelectItem>
                        <SelectItem value="relocation">Relocating to Austin</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="message">Additional Details</Label>
                    <Textarea
                      id="message"
                      value={formData.message}
                      onChange={(e) => handleInputChange('message', e.target.value)}
                      placeholder="Tell us about your ideal home, preferred neighborhoods, timeline, etc."
                      rows={4}
                    />
                  </div>
                  
                  <Button type="submit" className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                    Get Started - Contact Me
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                  
                  <p className="text-xs text-muted-foreground text-center">
                    By submitting this form, you agree to be contacted by YellowFin Real Estate regarding 
                    your home buying needs. We respect your privacy and will never share your information.
                  </p>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ContactSection;
