import { PROMPT_MAX } from '../constants';

interface OrbFrontFaceProps {
  isFocused: boolean;
  isDivining: boolean;
  isHidden: boolean;
  textareaId: string;
  validationId: string;
  charCountId: string;
  value: string;
  onChange: (value: string) => void;
  onFocus: () => void;
  onBlur: () => void;
  onSubmit: () => void;
  isSubmitDisabled: boolean;
}

export function OrbFrontFace({
  isFocused,
  isDivining,
  isHidden,
  textareaId,
  validationId,
  charCountId,
  value,
  onChange,
  onFocus,
  onBlur,
  onSubmit,
  isSubmitDisabled,
}: OrbFrontFaceProps) {
  const faceClasses = [
    'orb-face orb-face--front',
    isFocused && 'orb--focused',
    isDivining && 'orb--divining',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={faceClasses} aria-hidden={isHidden}>
      <div className="orb-lens-window">
        <textarea
          id={textareaId}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={onFocus}
          onBlur={onBlur}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if (!isSubmitDisabled) onSubmit();
            }
          }}
          placeholder="What happens next in the world?"
          maxLength={PROMPT_MAX}
          aria-describedby={`${validationId} ${charCountId}`}
          aria-invalid={value.length > 0 && value.length < 10}
          tabIndex={isHidden ? -1 : 0}
          className="orb-lens-input"
        />
      </div>
    </div>
  );
}
