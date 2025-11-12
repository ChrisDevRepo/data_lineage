import React from 'react';

type QuestionMarkIconProps = {
  size?: number;
  title?: string;
};

export const QuestionMarkIcon = React.memo(({ size = 20, title = 'Phantom Object (Not in catalog)' }: QuestionMarkIconProps) => {
  return (
    <span
      className="phantom-icon inline-block"
      title={title}
      style={{ fontSize: `${size}px`, lineHeight: 1 }}
    >
      👻
    </span>
  );
});
