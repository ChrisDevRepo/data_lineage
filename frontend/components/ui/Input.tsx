import React from 'react';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: 'default' | 'search';
  error?: boolean;
  icon?: 'search' | 'none';
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ variant = 'default', error = false, icon = 'none', fullWidth = false, className = '', ...props }, ref) => {
    const baseClasses = 'h-9 px-3 bg-white border rounded-md text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-600';
    const variantClasses = {
      default: '',
      search: 'pl-9',
    };
    const errorClasses = error ? 'border-red-300 focus:ring-red-600' : 'border-gray-300';
    const widthClasses = fullWidth ? 'w-full' : '';
    const disabledClasses = 'disabled:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50';

    const combinedClasses = `${baseClasses} ${variantClasses[variant]} ${errorClasses} ${widthClasses} ${disabledClasses} ${className}`.trim();

    return (
      <div className={`relative ${fullWidth ? 'w-full' : ''}`}>
        {icon === 'search' && (
          <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        )}
        <input
          ref={ref}
          className={combinedClasses}
          {...props}
        />
      </div>
    );
  }
);

Input.displayName = 'Input';
