import React from 'react';

/**
 * Checkbox Component
 *
 * A unified checkbox with consistent styling and optional label.
 */

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  description?: string;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  label,
  description,
  className = '',
  id,
  disabled = false,
  ...props
}) => {
  // Generate ID if not provided (for label association)
  const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  // Base checkbox styles
  const checkboxStyles = 'w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-2 focus:ring-primary-600 focus:ring-offset-0 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed';

  if (!label && !description) {
    // Standalone checkbox without label
    return (
      <input
        type="checkbox"
        id={checkboxId}
        className={`${checkboxStyles} ${className}`}
        disabled={disabled}
        {...props}
      />
    );
  }

  // Checkbox with label
  return (
    <label
      htmlFor={checkboxId}
      className={`flex items-start gap-2 cursor-pointer ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input
        type="checkbox"
        id={checkboxId}
        className={`${checkboxStyles} ${className} mt-0.5`}
        disabled={disabled}
        {...props}
      />
      <div className="flex-1">
        {label && (
          <span className="text-sm text-gray-800 select-none">
            {label}
          </span>
        )}
        {description && (
          <p className="text-xs text-gray-500 mt-0.5 select-none">
            {description}
          </p>
        )}
      </div>
    </label>
  );
};
