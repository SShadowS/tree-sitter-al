page 50100 "Selftest Card"
{
    PageType = Card;
    SourceTable = "Selftest Customer";

    layout
    {
        area(Content)
        {
            group(General)
            {
                field("No."; Rec."No.")
                {
                    ApplicationArea = All;
                }
            }
        }
    }

    actions
    {
        area(Processing)
        {
            action(DoIt)
            {
                ApplicationArea = All;

                trigger OnAction()
                begin
                    Message('done');
                end;
            }
        }
    }
}
