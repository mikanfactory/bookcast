create table if not exists project (
  id integer primary key generated always as identity,
  filename text not null,
  max_page_number integer not null,
  created_at timestamp with time zone default now() not null
);

