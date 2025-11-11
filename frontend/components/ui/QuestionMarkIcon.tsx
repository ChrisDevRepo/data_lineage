import React from 'react';

type QuestionMarkIconProps = {
  size?: number;
  title?: string;
};

export const QuestionMarkIcon = React.memo(({ size = 20, title = 'Phantom Object (Not in catalog)' }: QuestionMarkIconProps) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className="phantom-icon"
      title={title}
    >
      <circle cx="12" cy="12" r="10" fill="#ff9800" opacity="0.95" />
      <text
        x="12"
        y="17"
        fontSize="16"
        fontWeight="bold"
        fill="white"
        textAnchor="middle"
        fontFamily="Arial, sans-serif"
      >
        ?
      </text>
    </svg>
  );
});
