import { useMemo } from "react";

const PARTICLE_COUNT = 24;

interface ParticleStyle {
  left: string;
  width: string;
  height: string;
  animationDuration: string;
  animationDelay: string;
  opacity: number;
}

function generateParticles(): ParticleStyle[] {
  return Array.from({ length: PARTICLE_COUNT }, () => {
    const size = 2 + Math.random() * 3;
    return {
      left: `${Math.random() * 100}%`,
      width: `${size}px`,
      height: `${size}px`,
      animationDuration: `${12 + Math.random() * 18}s`,
      animationDelay: `${Math.random() * 15}s`,
      opacity: 0.15 + Math.random() * 0.25,
    };
  });
}

export function Particles() {
  const particles = useMemo(() => generateParticles(), []);

  return (
    <div className="particles-container" aria-hidden="true">
      {particles.map((style, i) => (
        <div key={i} className="particle" style={style} />
      ))}
    </div>
  );
}
