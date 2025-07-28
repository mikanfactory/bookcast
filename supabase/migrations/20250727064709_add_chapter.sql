create table if not exists chapter (
  id integer primary key generated always as identity,
  project_id integer not null references project(id) on delete cascade,
  start_page integer not null,
  end_page integer not null,
  created_at timestamp with time zone default now() not null
);

