interface CopyrightLinkProps {
  className?: string;
}

export const COPYRIGHT_TEXT = "Created by Alex Lignola - Release 1.0.3  - © 2026 Audio Track Studio - All rights reserved.";
export const COPYRIGHT_URL = "https://www.youtube.com/@AngoloInformatico";

export function CopyrightLink({ className = "" }: CopyrightLinkProps) {
  return (
    <a
      aria-label="Apri il canale YouTube Angolo Informatico"
      className={`copyright-link ${className}`.trim()}
      href={COPYRIGHT_URL}
      rel="noopener noreferrer"
      target="_blank"
    >
      {COPYRIGHT_TEXT}
    </a>
  );
}
