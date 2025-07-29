create table if not exists chapter (
  id integer primary key generated always as identity,
  project_id integer not null references project(id) on delete cascade,
  chapter_number integer not null,
  start_page integer not null,
  end_page integer not null,
  extracted_text text not null,
  created_at timestamp with time zone default now() not null
);

