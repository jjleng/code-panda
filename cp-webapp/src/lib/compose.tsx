import { ComponentType, PropsWithChildren } from 'react';

type Provider = ComponentType<PropsWithChildren>;

export const compose = (...providers: Provider[]) => {
  return ({ children }: PropsWithChildren) =>
    providers.reduceRight((child, Provider) => <Provider>{child}</Provider>, children);
};
