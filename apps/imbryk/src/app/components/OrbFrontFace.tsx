import { Textarea } from '@/components/ui/textarea';
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
      <Textarea
        id={textareaId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={onFocus}
        onBlur={onBlur}
        placeholder="What happens next in the world?"
        maxLength={PROMPT_MAX}
        aria-describedby={`${validationId} ${charCountId}`}
        aria-invalid={value.length > 0 && value.length < 10}
        tabIndex={isHidden ? -1 : 0}
        className="w-[70%] max-h-[60%] resize-none bg-transparent border-none text-white placeholder:text-white/40 text-center focus-visible:ring-0 focus-visible:ring-offset-0 scrollbar-thin"
      />
    </div>
  );
}
