export type ViewportClass = "phone-portrait" | "phone-landscape" | "tablet-portrait" | "tablet-landscape" | "desktop";

export function classifyViewport(width: number, height: number): ViewportClass {
  const shortSide = Math.min(width, height);
  const landscape = width > height;
  if (shortSide < 600) return landscape ? "phone-landscape" : "phone-portrait";
  if (shortSide < 1024) return landscape ? "tablet-landscape" : "tablet-portrait";
  return "desktop";
}
