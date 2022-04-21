#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h>
#include <signal.h>

#define PORT 8080

//struktura zawierająca informacje o klientach
struct user
{
    int cfd;
    char username[16];
};

//struktura zawierająca dane przekazywane do wątku
struct thread_data
{
    int is_sent;
    char msg[256];
    char receiver[16];
};

//tablica klientów
struct user users[32];
int last_usr_id=0;

//struktura przechowująca wiadomości do wysłania
struct thread_data to_send[32];
int last_msg_id=0;

//semafor kontrolujący czytanie i pisanie
pthread_mutex_t con_mutex = PTHREAD_MUTEX_INITIALIZER;

//funkcja zliczająca ukośniki
int count_slash(char msg[])
{
    int count=0;
    
    for(int i=0;i<256;i++)
    {
        if(msg[i]=='/')
        {
            count++;
            
            if(count==4)
            {
                return count;
            }
        }
    }
    
    return count;
}

//funkcja sprawdzająca czy użytkownik jest zalogowany i uaktualniająca jego deskryptor
int isOnline(char usr[], int cfd)
{
    int is_online=0;
    
    for(int i=0;i<last_usr_id;i++)
    {
        if(!strcmp(usr,users[i].username))
        {
            users[i].cfd=cfd;
            is_online=1;
	     return is_online;
        }
    }
    
    return is_online;
}

//funkcja czyszcząca tablicę to_send
void cleanup()
{
    int counter=0;
    
    for(int i=0;i<32;i++)
    {
        if(!to_send[i].is_sent)
        {
            strcpy(to_send[counter].receiver,to_send[i].receiver);
            strcpy(to_send[counter].msg,to_send[i].msg);
            to_send[i].is_sent=0;
            counter++;
        }
                
        for(int j=0;j<16;j++)
        {
            to_send[i].receiver[j]=0;
        }
    }
    
    last_msg_id=counter;
}

//funkcja znajdująca odpowiedni element w przesłanej wiadomości
char* findElement(char msg[])
{
    int i=2;
    int j=0;
    static char element[16];
    
    //dopóki nie natrafisz na znak / przepisuj
    while(msg[i]!='/')
    {
        element[j]=msg[i];
        i++;
        j++;
    }
    
    //uzupelnij pozostałość pustymi znakami
    for(int k = j;k<16;k++)
    {
        element[k]=0;
    }
    
    return element;
}

//funkcja do wylogowywania
void logout(char usr[])
{
    for(int i=0;i<last_usr_id;i++)
    {
        if(!strcmp(usr,users[i].username))
        {
            users[i].cfd=-1;
        }
    }
}

//funkcja wysylajaca uzytkownikowi liste uzytkownikow
void send_user_list(char usr[]){
	char list[256]={0};	
	for(int i = 0; i<last_usr_id;i++){	
		strcat(list, users[i].username);
		strcat(list,",");
	}
	for(int i = 0; i<last_usr_id;i++){
                if(!strcmp(users[i].username, usr)){
                        write(users[i].cfd, list, sizeof(list));
                }
        }

}

//funkcja przetwarzająca dane wysłane przez uzytkownika
void handleInput(char msg[],int fd)
{
    printf("%s\n", msg);
    //w zależności od akcji wybranej przez uzytkownika
    switch(msg[0])
    {
        //dodanie do tablicy zalogowanych uzytkownikow
        case 'L': ;
            
            //nazwa użytkownika który się loguje
            char usr[16]={0};
            
            //znalezienie użytkownika w wiadomości
            strcpy(usr,findElement(msg));
            
            //sprawdzenie czy użytkownik jest już na liście zalogowanych 
            int find_result=isOnline(usr,fd);
            //jeśli nie, to dopisanie użytkownika
            if(!find_result)
            {
                users[last_usr_id].cfd=fd;
                strcpy(users[last_usr_id].username,usr);
                last_usr_id++;
            }
            
            break;
            
        //odebranie wiadomości i zapisanie jej do przekazania do odbiorcy
        case 'M': ;
            
            //odbiorca wiadomości
            char r[16]={0};
            
            strcpy(r,findElement(msg));
            
            //wypełnienie struktury zawierającej wiadomość do wysłania
            strcpy(to_send[last_msg_id].msg,msg);
            strcpy(to_send[last_msg_id].receiver,r);
            to_send[last_msg_id].is_sent=0;
            last_msg_id++;
            if(last_msg_id==32)
            {
                cleanup();
            }
            
            break;
        
	case 'U': ;
	    char user[16]={0};
	    strcpy(user,findElement(msg));
	    send_user_list(user);
	    break;

        case 'W': ;
            
            char userr[16]={0};
            
            strcpy(userr,findElement(msg));

            logout(userr);
            
            break;
    }
}

//funkcja odbierająca wiadomości
void receive(int fd)
{
    //liczba znaków '/' w odebranym buforze
    int char_number;
    int size=2;
    
    char rec_msg[256]={0};
    char rec_buf[256]={0};
        
    pthread_mutex_lock(&con_mutex);
    read(fd,rec_msg,256);
    pthread_mutex_unlock(&con_mutex);
    
    if(rec_msg[0]=='\0')
    {
        return;
    }
    if(rec_msg[0]=='M'){
    	size = 4;
    }
    
    char_number=count_slash(rec_msg);
    
    strcpy(rec_buf,rec_msg);
    while(char_number!=size)
    {
        char rec_msg[256]={0};
        
        pthread_mutex_lock(&con_mutex);
        read(fd,rec_msg,256);
        pthread_mutex_unlock(&con_mutex);
        
        char_number+=count_slash(rec_msg);
        
        strcat(rec_buf,rec_msg);
    }
    
    handleInput(rec_buf,fd);
}

//funkcja opisującą zachowanie wątku
void *MainThreadBehavior(void *t_data)
{   
    while(1)
    {
        pthread_detach(pthread_self());
        
        for(int i=0;i<last_usr_id;i++)
        {
            //jeżeli klient nie jest odłączony
            if(users[i].cfd!=-1)
            {
                receive(users[i].cfd);
                
                //wysłanie wszystkich wiadomości do odbiorcy
                for(int j=0;j<last_msg_id;j++)
                {
                    if(!strcmp(users[i].username, to_send[j].receiver))
                    {
                        if(!to_send[j].is_sent)
                        {   
                            write(users[i].cfd, to_send[j].msg,256);   
                            to_send[j].is_sent=1;
                        }
                    }
                }
            
            }
                    
        }	
    }
    pthread_exit(NULL);
}

//funkcja obsługująca połączenie z nowym klientem
void handleConnection(int cfd) {
    //bufor na wiadomosc od klienta
    char msg[256]={0};

    //odczytanie danych i przekazanie ich do funkcji zajmującej się ich przetwarzaniem
    read(cfd,msg,256);
    
    pthread_mutex_lock(&con_mutex);
    handleInput(msg,cfd);
    
    fcntl(cfd, F_SETFL, O_NONBLOCK);
    pthread_mutex_unlock(&con_mutex);
}

int main(int argc, char* argv[])
{
   int sfd;
   int cfd;
   int bind_res;
   int listen_res;
   char reuse_addr_val = 1;
   struct sockaddr_in server_address;

   //inicjalizacja gniazda serwera
   
   memset(&server_address, 0, sizeof(struct sockaddr));
   server_address.sin_family = AF_INET;
   server_address.sin_addr.s_addr = htonl(INADDR_ANY);
   server_address.sin_port = htons(PORT);

   sfd = socket(AF_INET, SOCK_STREAM, 0);
   if (sfd < 0)
   {
       exit(1);
   }
   
   setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse_addr_val, sizeof(reuse_addr_val));

   bind_res = bind(sfd, (struct sockaddr*)&server_address, sizeof(struct sockaddr));
   if (bind_res < 0)
   {
       exit(1);
   }

   listen_res = listen(sfd, 15);
   if (listen_res < 0) {
       exit(1);
   }
   
    //wynik funkcji tworzącej wątek
    int create_res = 0;

    //uchwyt na wątek
    pthread_t thread2;
    
    //dane, które zostaną przekazane do wątku
    struct thread_data* t_data_m=malloc(sizeof(struct thread_data));

    create_res = pthread_create(&thread2, NULL, MainThreadBehavior, (void *)t_data_m);
    if (create_res){
       exit(-1);
    }

    while(1)
    {
       cfd = accept(sfd, NULL, NULL);
       if (cfd < 0)
       {
           exit(1);
       }
       handleConnection(cfd);
    }

    close(sfd);
    return(0);
}
