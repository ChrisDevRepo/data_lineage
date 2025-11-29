import React from 'react';

type QuestionMarkIconProps = {
  size?: number;
  title?: string;
};

export const QuestionMarkIcon = React.memo(({ size = 20, title = 'Phantom Object (Not in catalog)' }: QuestionMarkIconProps) => {
  return (
    <svg
      className="phantom-icon inline-block"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      title={title}
    >
      {/* Dashed circle */}
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="#f97316"
        strokeWidth="2"
        strokeDasharray="4 2"
        fill="none"
      />
      {/* Question mark - simplified */}
      <text
        x="12"
        y="17"
        textAnchor="middle"
        fontSize="14"
        fontWeight="bold"
        fill="#f97316"
      >
        ?
      </text>
    </svg>
  );
});
