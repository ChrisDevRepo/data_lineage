import React from 'react';

/**
 * Select Component
 *
 * A unified select dropdown with consistent styling.
 * Replaces all custom select implementations across the app.
 */

type SelectSize = 'sm' | 'md' | 'lg';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  size?: SelectSize;
  children: React.ReactNode;
  fullWidth?: boolean;
}

export const Select: React.FC<SelectProps> = ({
  size = 'md',
  children,
  fullWidth = false,
  className = '',
  disabled = false,
  ...props
}) => {
  // Base styles - always applied
  const baseStyles = 'appearance-none bg-white border border-gray-300 rounded-lg text-gray-800 font-semibold cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100';

  // Size styles
  const sizeStyles: Record<SelectSize, string> = {
    sm: 'h-8 px-3 py-1 text-xs',
    md: 'h-10 px-4 py-2 text-sm',
    lg: 'h-12 px-6 py-3 text-base',
  };

  // Width style
  const widthStyle = fullWidth ? 'w-full' : '';

  // Combine all styles
  const combinedStyles = `${baseStyles} ${sizeStyles[size]} ${widthStyle} ${className}`;

  return (
    <div className={`relative ${fullWidth ? 'w-full' : 'inline-block'}`}>
      <select
        className={combinedStyles}
        disabled={disabled}
        {...props}
      >
        {children}
      </select>
      {/* Dropdown arrow icon */}
      <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
};
