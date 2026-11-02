ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS section_title VARCHAR(500);

ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS start_char INTEGER;

ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS end_char INTEGER;

ALTER TABLE chunks
ADD CONSTRAINT chk_chunks_start_char
CHECK (start_char IS NULL OR start_char >= 0);

ALTER TABLE chunks
ADD CONSTRAINT chk_chunks_end_char
CHECK (end_char IS NULL OR end_char >= 0);

ALTER TABLE chunks
ADD CONSTRAINT chk_chunks_char_range
CHECK (
    start_char IS NULL
    OR end_char IS NULL
    OR end_char >= start_char
);