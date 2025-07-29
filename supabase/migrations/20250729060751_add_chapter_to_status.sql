alter table chapter add column if not exists status varchar(100) not null default 'not_started';
