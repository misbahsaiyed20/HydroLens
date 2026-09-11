type IconProps = { className?: string; strokeWidth?: number };

const base = "1.8";

function svg(children: React.ReactNode, { className, strokeWidth }: IconProps = {}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth ?? base}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className ?? "h-4 w-4"}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export const Icon = {
  Droplet: (p: IconProps = {}) => svg(<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11Z" />, p),
  Pin: (p: IconProps = {}) =>
    svg(
      <>
        <path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21Z" />
        <circle cx="12" cy="9.5" r="2.3" />
      </>,
      p
    ),
  Layers: (p: IconProps = {}) =>
    svg(
      <>
        <path d="m12 3 8 4.5-8 4.5-8-4.5L12 3Z" />
        <path d="m4 12 8 4.5 8-4.5" />
        <path d="m4 16.5 8 4.5 8-4.5" />
      </>,
      p
    ),
  Gauge: (p: IconProps = {}) =>
    svg(
      <>
        <path d="M4.5 19a8.5 8.5 0 1 1 15 0" />
        <path d="M12 13 15 9" />
        <circle cx="12" cy="13" r="0.9" fill="currentColor" stroke="none" />
      </>,
      p
    ),
  Warning: (p: IconProps = {}) =>
    svg(
      <>
        <path d="M10.6 3.9 2.9 18a1.6 1.6 0 0 0 1.4 2.4h15.4a1.6 1.6 0 0 0 1.4-2.4L13.4 3.9a1.6 1.6 0 0 0-2.8 0Z" />
        <path d="M12 9.5v4" />
        <circle cx="12" cy="16.5" r="0.9" fill="currentColor" stroke="none" />
      </>,
      p
    ),
  Check: (p: IconProps = {}) => svg(<path d="m4.5 12.5 5 5 10-11" />, p),
  Shield: (p: IconProps = {}) =>
    svg(<path d="M12 3.5 19 6v6c0 4.4-2.9 7.6-7 8.5-4.1-.9-7-4.1-7-8.5V6l7-2.5Z" />, p),
  FileCheck: (p: IconProps = {}) =>
    svg(
      <>
        <path d="M7 3.5h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-16a1 1 0 0 1 1-1Z" />
        <path d="M14 3.5v4h4" />
        <path d="m9 14 2 2 4-4.5" />
      </>,
      p
    ),
  Upload: (p: IconProps = {}) =>
    svg(
      <>
        <path d="M12 15V4" />
        <path d="m7 8.5 5-4.5 5 4.5" />
        <path d="M4.5 15.5V19a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-3.5" />
      </>,
      p
    ),
  Image: (p: IconProps = {}) =>
    svg(
      <>
        <rect x="3.5" y="4.5" width="17" height="15" rx="2" />
        <circle cx="8.5" cy="9.5" r="1.4" />
        <path d="m5 17 4.5-4.5a1.5 1.5 0 0 1 2 0L15 16l1.5-1.5a1.5 1.5 0 0 1 2 0L20.5 16" />
      </>,
      p
    ),
  Clock: (p: IconProps = {}) => svg(<><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>, p),
  ArrowRight: (p: IconProps = {}) => svg(<><path d="M4.5 12h15" /><path d="m13 6 6 6-6 6" /></>, p),
  ChevronDown: (p: IconProps = {}) => svg(<path d="m5.5 8.5 6.5 7 6.5-7" />, p),
  Search: (p: IconProps = {}) => svg(<><circle cx="10.5" cy="10.5" r="6.5" /><path d="m20 20-4.3-4.3" /></>, p),
  Map: (p: IconProps = {}) =>
    svg(
      <>
        <path d="M9 4.5 4 6.5v13l5-2 6 2 5-2v-13l-5 2-6-2Z" />
        <path d="M9 4.5v13" />
        <path d="M15 6.5v13" />
      </>,
      p
    ),
  List: (p: IconProps = {}) =>
    svg(
      <>
        <path d="M8 6.5h12" />
        <path d="M8 12h12" />
        <path d="M8 17.5h12" />
        <circle cx="4" cy="6.5" r="0.9" fill="currentColor" stroke="none" />
        <circle cx="4" cy="12" r="0.9" fill="currentColor" stroke="none" />
        <circle cx="4" cy="17.5" r="0.9" fill="currentColor" stroke="none" />
      </>,
      p
    ),
  X: (p: IconProps = {}) => svg(<path d="M6 6l12 12M18 6 6 18" />, p),
  Menu: (p: IconProps = {}) => svg(<><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" /></>, p),
};
