drop trigger if exists "handle_project_updated_at" on "public"."project";

alter table "public"."project" drop column "status";

alter table "public"."project" drop column "updated_at";


