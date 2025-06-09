export interface Listing {
  id: number;
  image: string;
  price: string;
  address: string;
  beds: number;
  baths: number;
  sqft: string;
  neighborhood: string;
}

export const featuredListings: Listing[] = [
  {
    id: 1,
    image: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    price: "$485,000",
    address: "2847 Oak Hill Drive, Austin, TX 78704",
    beds: 3,
    baths: 2,
    sqft: "1,850",
    neighborhood: "South Austin"
  },
  {
    id: 2,
    image: "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    price: "$675,000",
    address: "1523 Cedar Park Way, Austin, TX 78731",
    beds: 4,
    baths: 3,
    sqft: "2,400",
    neighborhood: "Northwest Hills"
  },
  {
    id: 3,
    image: "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    price: "$525,000",
    address: "4102 Mueller Blvd, Austin, TX 78723",
    beds: 3,
    baths: 2.5,
    sqft: "2,100",
    neighborhood: "Mueller"
  },
  {
    id: 4,
    image: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
    price: "$750,000",
    address: "856 Westlake Drive, Austin, TX 78746",
    beds: 4,
    baths: 3.5,
    sqft: "2,800",
    neighborhood: "Westlake"
  }
];
