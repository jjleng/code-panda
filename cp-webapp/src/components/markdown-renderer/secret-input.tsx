import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useProject } from '@/context';
import { setProjectSecretApiV1ProjectsProjectIdSecretsPostMutation } from '@/generated/agent/@tanstack/react-query.gen';
import { useToast } from '@/hooks/use-toast';
import { useMutation } from '@tanstack/react-query';
import { Key } from 'lucide-react';
import React, { memo, useState } from 'react';

export interface SecretInputProps {
  name: string;
  description: string;
  children: React.ReactNode;
}

const SecretInput = memo(({ name, description, children }: SecretInputProps) => {
  const [open, setOpen] = useState(false);
  const [secretValue, setSecretValue] = useState('');
  const { projectId } = useProject();
  const { toast } = useToast();

  // Set up the mutation for saving secrets
  const secretMutation = useMutation(setProjectSecretApiV1ProjectsProjectIdSecretsPostMutation());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!projectId || !secretValue.trim()) {
      return;
    }

    try {
      await secretMutation.mutateAsync({
        headers: {
          'X-CP-Project-ID': projectId,
        },
        path: {
          project_id: projectId,
        },
        body: {
          name: name,
          value: secretValue,
        },
      });

      toast({
        title: 'Secret saved',
        description: `The secret "${name}" was successfully saved.`,
      });

      setOpen(false);
      // Reset the form
      setSecretValue('');
    } catch (error) {
      console.error('Error saving secret:', error);
      toast({
        title: 'Failed to save secret',
        description: 'There was an error saving your secret. Please try again.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="flex flex-col gap-1.5">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className="inline-flex w-full items-center gap-2">
            <Key className="h-4 w-4" />
            {children}
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Enter Secret Value</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="secret">{name}</Label>
                <Input
                  id="secret"
                  type="password"
                  value={secretValue}
                  onChange={e => setSecretValue(e.target.value)}
                  autoFocus
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={secretMutation.isPending || !secretValue.trim()}>
                {secretMutation.isPending ? 'Saving...' : 'Submit'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
});

SecretInput.displayName = 'SecretInput';

export { SecretInput };
