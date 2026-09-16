export const hostedDemo = (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_HOSTED_DEMO === "true";
