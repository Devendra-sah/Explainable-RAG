import { useEffect, useRef } from "react";
import { OceanEngine } from "./engine";

export function AsciiOcean({ className = "" }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return undefined;
    const engine = new OceanEngine(canvasRef.current);
    return () => engine.destroy();
  }, []);

  return <canvas ref={canvasRef} aria-hidden="true" className={`ascii-ocean ${className}`} />;
}
