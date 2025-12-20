drop table if exists folios;
create table folios (
  name varchar(200) not null primary key,
  prompt text not null,
  query  text not null,
  params text not null
);

drop table if exists the_accounts;
create table the_accounts (
  id uuid not null primary key,
  name text,
  notes text
);

.mode csv
.import import.csv folios -skip 1
.import accounts.csv the_accounts -skip 1
