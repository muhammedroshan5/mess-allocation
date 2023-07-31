drop table if exists student;
create table student (
id integer primary key autoincrement,
username text not null,
name text not null,
pwd text not null,
gender text,
hostel text,
email text,
room text,
mess text,
due integer default 0);

create table admin (
id integer primary key autoincrement,
username text not null,
name text not null,
pwd text not null,
phno text);

create table mess (
id integer primary key autoincrement,
name text not null,
capacity integer not null,
owner text,
category character not null);
