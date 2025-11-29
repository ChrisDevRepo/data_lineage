import React from 'react';

/**
 * Spinner Component
 *
 * A unified loading spinner with consistent styling.
 * Replaces duplicate spinner implementations across the app.
 */

type SpinnerSize = 'sm' | 'md' | 'lg';
type SpinnerVariant = 'primary' | 'light';

interface SpinnerProps {
  size?: SpinnerSize;
  variant?: SpinnerVariant;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  className = '',
}) => {
  // Size styles
  const sizeStyles: Record<SpinnerSize, string> = {
    sm: 'w-5 h-5 border-2',
    md: 'w-10 h-10 border-4',
    lg: 'w-16 h-16 border-4',
  };

  // Variant styles
  const variantStyles: Record<SpinnerVariant, string> = {
    primary: 'border-gray-300 border-t-primary-600',
    light: 'border-gray-200 border-t-white',
  };

  // Combine styles
  const combinedStyles = `${sizeStyles[size]} ${variantStyles[variant]} rounded-full animate-spin ${className}`;

  return <div className={combinedStyles} />;
};

/**
 * SpinnerContainer Component
 *
 * A centered container with spinner and optional message.
 * Common pattern for loading states.
 */

interface SpinnerContainerProps {
  message?: string;
  size?: SpinnerSize;
  variant?: SpinnerVariant;
}

export const SpinnerContainer: React.FC<SpinnerContainerProps> = ({
  message = 'Loading...',
  size = 'md',
  variant = 'primary',
}) => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-gray-500">
      <Spinner size={size} variant={variant} />
      {message && <p className="mt-4 text-sm">{message}</p>}
    </div>
  );
};
