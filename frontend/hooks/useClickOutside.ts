import { useEffect, RefObject } from 'react';

/**
 * Custom hook to handle clicks outside a referenced element.
 * Useful for closing dropdowns, modals, and other UI elements.
 *
 * @param ref - React ref to the element to monitor
 * @param handler - Callback function to execute when click occurs outside
 */
export function useClickOutside(
  ref: RefObject<HTMLElement>,
  handler: () => void
) {
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [ref, handler]);
}
