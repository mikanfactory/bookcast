alter table project add column if not exists status varchar(100) not null default 'not_started';

create extension if not exists moddatetime schema extensions;
alter table project add column if not exists updated_at timestamp with time zone default now() not null;
create trigger handle_project_updated_at before update on project
  for each row execute procedure moddatetime (updated_at);
