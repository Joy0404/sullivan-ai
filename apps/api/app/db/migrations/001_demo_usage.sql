CREATE TABLE IF NOT EXISTS public.demo_usage (
    ip_hash text NOT NULL,
    usage_day date NOT NULL,
    count smallint NOT NULL CHECK (count BETWEEN 0 AND 3),
    PRIMARY KEY (ip_hash, usage_day)
);
CREATE INDEX IF NOT EXISTS demo_usage_day_idx ON public.demo_usage (usage_day);
