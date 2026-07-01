declare module 'plotly.js-dist-min' {
  export type Data = Record<string, unknown>;
  export type Layout = Record<string, unknown>;
  export type Config = Record<string, unknown>;
  export type PlotMarker = Record<string, unknown>;

  export function react(
    root: HTMLElement,
    data: Data[],
    layout?: Partial<Layout>,
    config?: Partial<Config>
  ): Promise<void>;

  export function newPlot(
    root: HTMLElement,
    data: Data[],
    layout?: Partial<Layout>,
    config?: Partial<Config>
  ): Promise<void>;

  export function purge(root: HTMLElement): void;
}
