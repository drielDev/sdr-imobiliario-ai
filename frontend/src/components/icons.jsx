function base(props) {
  return {
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    ...props,
  };
}

export function IconBed(props) {
  return (
    <svg {...base(props)}>
      <path d="M2 18v-6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v6" />
      <path d="M2 18v2" />
      <path d="M22 18v2" />
      <path d="M2 12V8a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M12 12V9a1 1 0 0 1 1-1h6a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

export function IconBath(props) {
  return (
    <svg {...base(props)}>
      <path d="M9 6 6.5 3.5a1.5 1.5 0 0 0-2.5 1V11" />
      <path d="M4 11h16v2a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5Z" />
      <path d="M4 18v2" />
      <path d="M18 18v2" />
    </svg>
  );
}

export function IconCar(props) {
  return (
    <svg {...base(props)}>
      <path d="M5 12 6.6 7.2A2 2 0 0 1 8.5 6h7a2 2 0 0 1 1.9 1.2L19 12" />
      <path d="M2.5 12h19v5a1 1 0 0 1-1 1H17a1 1 0 0 1-1-1v-1H8v1a1 1 0 0 1-1 1H3.5a1 1 0 0 1-1-1Z" />
      <circle cx="7" cy="17" r="1.5" />
      <circle cx="17" cy="17" r="1.5" />
    </svg>
  );
}

export function IconRuler(props) {
  return (
    <svg {...base(props)}>
      <rect x="2.5" y="7" width="19" height="10" rx="1.5" />
      <path d="M7 7v3M11 7v3M15 7v3M19 7v3" />
    </svg>
  );
}

export function IconMapPin(props) {
  return (
    <svg {...base(props)}>
      <path d="M20 10c0 5.5-8 12-8 12s-8-6.5-8-12a8 8 0 0 1 16 0Z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}

export function IconSearch(props) {
  return (
    <svg {...base(props)}>
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

export function IconChat(props) {
  return (
    <svg {...base(props)}>
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z" />
    </svg>
  );
}

export function IconClose(props) {
  return (
    <svg {...base(props)}>
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}

export function IconBuilding(props) {
  return (
    <svg {...base(props)}>
      <rect x="4" y="2.5" width="16" height="19" rx="1" />
      <path d="M9 22v-4h6v4" />
      <path d="M8 7h1M8 11h1M8 15h1M15 7h1M15 11h1M15 15h1" />
    </svg>
  );
}

export function IconHouse(props) {
  return (
    <svg {...base(props)}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5 10v10a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V10" />
    </svg>
  );
}

export function IconTag(props) {
  return (
    <svg {...base(props)}>
      <path d="M12.6 2.6a2 2 0 0 0-2.8 0L3 9.4a2 2 0 0 0 0 2.8l8.8 8.8a2 2 0 0 0 2.8 0l6.8-6.8a2 2 0 0 0 0-2.8Z" />
      <circle cx="8.5" cy="8.5" r="1.5" />
    </svg>
  );
}

export function IconArrowRight(props) {
  return (
    <svg {...base(props)}>
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </svg>
  );
}

export function IconSend(props) {
  return (
    <svg {...base(props)}>
      <path d="M22 2 11 13" />
      <path d="M22 2 15 22l-4-9-9-4 20-7Z" />
    </svg>
  );
}

export function IconExpand(props) {
  return (
    <svg {...base(props)}>
      <path d="M15 3h6v6" />
      <path d="M9 21H3v-6" />
      <path d="M21 3 14 10" />
      <path d="M3 21l7-7" />
    </svg>
  );
}

export function IconShrink(props) {
  return (
    <svg {...base(props)}>
      <path d="M9 3v6H3" />
      <path d="M15 21v-6h6" />
      <path d="M3 3l7 7" />
      <path d="M21 21l-7-7" />
    </svg>
  );
}
