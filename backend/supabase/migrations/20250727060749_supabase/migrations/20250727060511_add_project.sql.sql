revoke delete on table "public"."project" from "anon";

revoke insert on table "public"."project" from "anon";

revoke references on table "public"."project" from "anon";

revoke select on table "public"."project" from "anon";

revoke trigger on table "public"."project" from "anon";

revoke truncate on table "public"."project" from "anon";

revoke update on table "public"."project" from "anon";

revoke delete on table "public"."project" from "authenticated";

revoke insert on table "public"."project" from "authenticated";

revoke references on table "public"."project" from "authenticated";

revoke select on table "public"."project" from "authenticated";

revoke trigger on table "public"."project" from "authenticated";

revoke truncate on table "public"."project" from "authenticated";

revoke update on table "public"."project" from "authenticated";

revoke delete on table "public"."project" from "service_role";

revoke insert on table "public"."project" from "service_role";

revoke references on table "public"."project" from "service_role";

revoke select on table "public"."project" from "service_role";

revoke trigger on table "public"."project" from "service_role";

revoke truncate on table "public"."project" from "service_role";

revoke update on table "public"."project" from "service_role";

alter table "public"."project" drop constraint "project_pkey";

drop index if exists "public"."project_pkey";

drop table "public"."project";


