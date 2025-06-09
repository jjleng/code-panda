export interface Testimonial {
  name: string;
  text: string;
  rating: number;
  location: string;
}

export const testimonials: Testimonial[] = [
  {
    name: "Sarah & Mike Johnson",
    text: "YellowFin made our home buying experience seamless. Their knowledge of Austin neighborhoods was invaluable in finding our perfect home in Mueller.",
    rating: 5,
    location: "Mueller"
  },
  {
    name: "David Chen",
    text: "As a first-time buyer, I was overwhelmed by the process. The YellowFin team guided me every step of the way and found me an amazing condo downtown.",
    rating: 5,
    location: "Downtown Austin"
  },
  {
    name: "Jennifer Martinez",
    text: "Professional, responsive, and truly cared about finding us the right home. We couldn't be happier with our new place in South Austin!",
    rating: 5,
    location: "South Austin"
  }
];
