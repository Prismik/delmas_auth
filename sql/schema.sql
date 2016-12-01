
drop table if exists users;
create table users (
	email text not null,
	current_connect_attemp integer not null,
	force_pwd_change integer not null,
	locked_until integer not null,
	primary key ( email)
	);

drop table if exists roles;
create table roles(
	role text not null primary key
	);

drop table if exists user_roles;
create table user_roles(
	user text not null,
	role text not null,
	primary key ( user, role ),
	foreign key ( user ) references users(email),
	foreign key ( role ) references roles(role)
	);

drop table if exists passwords;
create table passwords(
	user text not null,
	created_at integer not null,
	pwd text not null,
	hash_method text not null,
	primary key ( user, created_at)
	foreign key (user) references users(email)
	);

drop table if exists logs;
create table logs(
	type text not null,
	created_at text not null,
	detail text
	);

drop table if exists app_settings;
create table app_settings(
	user text not null,
	created_at integer not null,
	pwd_max_attempts integer not null,
	pwd_wait_time integer not null,
	pwd_lock integer not null,
	pwd_force_change_after_time integer,
	pwd_force_change_after_max_attempts integer,
	pwd_forbid_x_last integer not null,
	pwd_min_length integer not null,
	pwd_lower_and_upper integer not null,
	pwd_special_char integer not null,
	pwd_digit integer not null,
	pwd_current_hash_method text not null,
	foreign key (user) references users(email)
	);

insert into roles values ('admin'),('circle'),('square');

insert into users values ('circle@delmas.com', 0, 0, 0);
insert into user_roles values ('circle@delmas.com','circle');
insert into users values ('square@delmas.com', 0, 0, 0);
insert into user_roles values ('square@delmas.com','square');
insert into users values ('admin@delmas.com', 0, 0, 0);
insert into user_roles values ('admin@delmas.com','admin');

insert into passwords values ('circle@delmas.com',0,'f95fb05b9e045243e04ce7b5a182056cff355bff099c0623dc79458f1067d6fb:23237fe6d9f64b2e88104b7a9b59e88c','sha256*2');
insert into passwords values ('square@delmas.com',0,'2d62fcee96031a67fd99345e54f73dba2afb10ef6422efdc366c6732f328fc29:7cd8a77cd3b94801b88be1d1a431b109','sha256*2');
insert into passwords values ('admin@delmas.com',0,'009b8c219e30029b22ad571466e8d20a159b5383460286defe7bd09bcd83242f:34dba24cc4b240789f0906c9aefeea47','sha256*2');

insert into app_settings values ('admin@delmas.com', /* user */
  0, /* created_at */
  3, /* pwd_max_attempts */
  50, /* pwd_wait_time */
  0, /* pwd_lock */
  1000, /* pwd_force_change_after_time */
  1, /* pwd_force_change_after_max_attempts */
  2, /* pwd_forbid_x_last */
  6, /* pwd_min_length */ 
  1, /* pwd_lower_and_upper */
  0, /* pwd_special_char */
  1, /* pwd_digit */ 
  'sha256*2' /* pwd_current_hash_method */);
