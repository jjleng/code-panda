import { LucideIcon } from 'lucide-react';
import { Coffee, Building, GraduationCap, TreePine } from 'lucide-react';

export interface Neighborhood {
  name: string;
  description: string;
  icon: LucideIcon;
  highlights: string[];
}

export const neighborhoods: Neighborhood[] = [
  {
    name: "South Austin",
    description: "Trendy area known for food trucks, live music venues, and eclectic culture",
    icon: Coffee,
    highlights: ["Food Scene", "Music Venues", "Zilker Park"]
  },
  {
    name: "Downtown",
    description: "Urban living with high-rise condos, business district, and nightlife",
    icon: Building,
    highlights: ["City Life", "Walkability", "Entertainment"]
  },
  {
    name: "Westlake",
    description: "Upscale suburban community with excellent schools and luxury homes",
    icon: GraduationCap,
    highlights: ["Top Schools", "Luxury Homes", "Family-Friendly"]
  },
  {
    name: "Mueller",
    description: "Master-planned community with parks, trails, and modern amenities",
    icon: TreePine,
    highlights: ["New Development", "Green Spaces", "Community Feel"]
  }
];
