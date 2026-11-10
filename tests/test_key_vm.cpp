#include "lua.h"
#include "lualib.h"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <iostream>
#include <string>
#include <vector>
static std::string testRoot;
static int requests=0, grants=0;
static int identity(lua_State* L){lua_pushvalue(L,1);return 1;}
static int hwid(lua_State* L){lua_pushliteral(L,"test-hwid");return 1;}
static int jsonencode(lua_State* L){lua_pushliteral(L,"{}");return 1;}
static int noop(lua_State*){return 0;}
static int grant(lua_State*){++grants;return 0;}
static int env(lua_State* L){lua_getglobal(L,"test_env");return 1;}
static int yes(lua_State* L){lua_pushboolean(L,true);return 1;}
static int request(lua_State* L){++requests;lua_newtable(L);lua_pushinteger(L,429);lua_setfield(L,-2,"StatusCode");lua_pushliteral(L,"{}");lua_setfield(L,-2,"Body");return 1;}
static void check(lua_State* L,int status){if(status)throw std::runtime_error(lua_tostring(L,-1));}
static void load(lua_State* L,int id){std::ifstream f(testRoot+"/test-proto-"+std::to_string(id)+".luauc",std::ios::binary);std::string b((std::istreambuf_iterator<char>(f)),{});check(L,luau_load(L,"=key-test",b.data(),b.size(),0));check(L,lua_pcall(L,0,1,0));}
static void cval(lua_State* L,int id,lua_CFunction fn){lua_pushcfunction(L,fn,"test-stub");if(!lua_setupvalue(L,-2,id))throw std::runtime_error("upvalue");}
static void nilval(lua_State* L,int id){lua_pushnil(L);if(!lua_setupvalue(L,-2,id))throw std::runtime_error("upvalue nil");}
static void tostringval(lua_State* L,int id){lua_getglobal(L,"tostring");lua_setupvalue(L,-2,id);}
static void subval(lua_State* L,int id){lua_getglobal(L,"string");lua_getfield(L,-1,"sub");lua_remove(L,-2);lua_setupvalue(L,-2,id);}
static void setup(lua_State* L,int id,bool busy=false){
 if(id==55){lua_pushboolean(L,busy);lua_setupvalue(L,-2,1);cval(L,2,noop);lua_pushinteger(L,1);lua_setupvalue(L,-2,3);tostringval(L,4);cval(L,5,identity);cval(L,6,hwid);cval(L,7,noop);subval(L,8);nilval(L,9);nilval(L,10);}
 else {lua_pushinteger(L,1);lua_setupvalue(L,-2,1);tostringval(L,2);cval(L,3,identity);cval(L,4,hwid);cval(L,5,jsonencode);cval(L,6,noop);cval(L,7,noop);nilval(L,8);subval(L,9);}
}
static void boolfield(lua_State* L,const char* name,bool b){lua_pushboolean(L,b);lua_setfield(L,-2,name);}
static void globalfield(lua_State* L,const char* field,const char* global){lua_getglobal(L,global);lua_setfield(L,-2,field);}
static void setupGrant(lua_State* L){
 lua_newtable(L);boolfield(L,"Enabled",true);lua_setglobal(L,"test_ui");
 lua_newtable(L);boolfield(L,"Visible",false);lua_setglobal(L,"test_sidebar");
 lua_newtable(L);globalfield(L,"Sidebar","test_sidebar");lua_setglobal(L,"test_root");
 lua_newtable(L);boolfield(L,"Visible",true);globalfield(L,"Parent","test_root");lua_setglobal(L,"test_parent");
 lua_newtable(L);globalfield(L,"Parent","test_parent");lua_setglobal(L,"test_frame");
 lua_newtable(L);globalfield(L,"Ui","test_ui");lua_setglobal(L,"test_outer");
 lua_newtable(L);boolfield(L,"Value",false);lua_setglobal(L,"test_animations");
 lua_newtable(L);boolfield(L,"is_unlocked",false);lua_newtable(L);lua_pushcfunction(L,grant,"End");lua_setfield(L,-2,"End");lua_setfield(L,-2,"rLib");lua_setglobal(L,"test_env");
 lua_pushcfunction(L,env,"uienv");lua_setglobal(L,"uienv");lua_pushcfunction(L,yes,"isinternalfile");lua_setglobal(L,"isinternalfile");lua_pushcfunction(L,noop,"runteleportscripts");lua_setglobal(L,"runteleportscripts");
 load(L,101);lua_getglobal(L,"test_outer");lua_setupvalue(L,-2,1);lua_getglobal(L,"test_animations");lua_setupvalue(L,-2,2);nilval(L,3);lua_getglobal(L,"test_frame");lua_setupvalue(L,-2,4);lua_setglobal(L,"GrantAccess");
}
static bool getbool(lua_State* L,const char* global,const char* field){lua_getglobal(L,global);lua_getfield(L,-1,field);bool b=lua_toboolean(L,-1);lua_pop(L,2);return b;}
static lua_State* state(){requests=grants=0;lua_State* L=luaL_newstate();luaL_openlibs(L);lua_pushcfunction(L,request,"request-stub");lua_setglobal(L,"GLOOPY_SAFE_REQUEST");return L;}
int main(int argc,char** argv){if(argc!=2)return 2;testRoot=argv[1];try{int tests=0;std::vector<std::string> keys={"@Icon_Crack","@Icon_Crack","@Icon_Crack","wrong-key","@icon_crack","","@Icon_Crack "," @Icon_Crack"};
 for(int id:{54,55})for(auto& key:keys){lua_State* L=state();load(L,id);setup(L,id);lua_pushlstring(L,key.data(),key.size());check(L,lua_pcall(L,1,1,0));bool expected=key=="@Icon_Crack";if(lua_type(L,-1)!=LUA_TBOOLEAN||bool(lua_toboolean(L,-1))!=expected||requests!=(expected?0:1))throw std::runtime_error("validator result/network mismatch for "+std::to_string(id)+"/"+key);lua_close(L);++tests;}
 {lua_State* L=state();load(L,55);setup(L,55,true);lua_pushliteral(L,"@Icon_Crack");check(L,lua_pcall(L,1,1,0));if(!lua_toboolean(L,-1)||requests)throw std::runtime_error("busy state blocked fixed key");lua_close(L);++tests;}
 for(auto& key:keys){lua_State* L=state();setupGrant(L);load(L,55);setup(L,55);lua_setglobal(L,"test_validator");load(L,107);load(L,106);lua_setupvalue(L,-2,1);lua_newtable(L);lua_pushlstring(L,key.data(),key.size());lua_setfield(L,-2,"Text");lua_setupvalue(L,-2,2);lua_getglobal(L,"test_validator");lua_setupvalue(L,-2,3);check(L,lua_pcall(L,0,0,0));bool expected=key=="@Icon_Crack"||key=="@Icon_Crack ";if(getbool(L,"test_env","is_unlocked")!=expected||getbool(L,"test_ui","Enabled")==expected||getbool(L,"test_parent","Visible")==expected||getbool(L,"test_sidebar","Visible")!=expected)throw std::runtime_error("actual GrantAccess UI state mismatch/"+key);if(grants!=(expected?1:0)||requests!=(expected?0:1))throw std::runtime_error("Continue callback mismatch/"+key);lua_close(L);++tests;}
 std::cout<<"PASS: "<<tests<<" Luau VM cases; fixed key succeeds without HTTP, actual sanitizer/Continue/GrantAccess handlers unlock the UI, other keys retain validation.\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<"\n";return 1;}}
