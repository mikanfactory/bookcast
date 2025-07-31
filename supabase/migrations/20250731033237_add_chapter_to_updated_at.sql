create extension if not exists moddatetime schema extensions;
alter table chapter add column if not exists updated_at timestamp with time zone default now() not null;
create trigger handle_chapter_updated_at before update on chapter
  for each row execute procedure moddatetime (updated_at);
