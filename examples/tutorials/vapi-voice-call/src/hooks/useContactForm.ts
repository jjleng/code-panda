import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/lib/supabaseClient';

export interface FormData {
  name: string;
  email: string;
  phone: string;
  interests: string;
  message: string;
}

export const useContactForm = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    phone: '',
    interests: '',
    message: ''
  });

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateForm = (): boolean => {
    // Basic validation
    if (!formData.name || !formData.email || !formData.phone) {
      toast({
        title: "Please fill in all required fields",
        description: "Name, email, and phone are required to get started.",
        variant: "destructive"
      });
      return false;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast({
        title: "Invalid email address",
        description: "Please enter a valid email address.",
        variant: "destructive"
      });
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      // Show loading toast
      toast({
        title: "Processing your request...",
        description: "We're setting up a call for you right now!",
      });

      // Call the Vapi edge function
      const { data, error } = await supabase.functions.invoke('vapi-call', {
        body: {
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          interests: formData.interests,
        }
      });

      if (error) {
        console.error('Error calling Vapi function:', error);
        toast({
          title: "Something went wrong",
          description: "We couldn't initiate the call right now. Please try calling us directly at (512) 555-0123.",
          variant: "destructive"
        });
        return;
      }

      // Success - call initiated
      toast({
        title: "Call initiated successfully! 📞",
        description: "Nancy from YellowFin will call you within the next few minutes to discuss your home buying needs.",
      });

      // Reset form
      setFormData({
        name: '',
        email: '',
        phone: '',
        interests: '',
        message: ''
      });

    } catch (error) {
      console.error('Unexpected error:', error);
      toast({
        title: "Something went wrong",
        description: "We couldn't initiate the call right now. Please try calling us directly at (512) 555-0123.",
        variant: "destructive"
      });
    }
  };

  return {
    formData,
    handleInputChange,
    handleSubmit
  };
};
